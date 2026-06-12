
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_eec4cbb19dd478c3277fe32ce404f9c0 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5a1eb0343590d6915ba5b22f68c41852 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Add a new transaction",css:({ ["margin"] : "0 10px 10px", ["padding"] : "11px", ["background"] : "#BF5AF2", ["color"] : "#fff", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["gap"] : "8px", ["boxShadow"] : "0 4px 16px rgba(191,90,242,0.38)", ["&:hover"] : ({ ["opacity"] : "0.9", ["boxShadow"] : "0 6px 22px rgba(191,90,242,0.38)" }), ["&:active"] : ({ ["transform"] : "scale(0.97)" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #fff", ["outlineOffset"] : "2px" }) }),onClick:on_click_5a1eb0343590d6915ba5b22f68c41852,role:"button",tabIndex:0},children)
    )
});
