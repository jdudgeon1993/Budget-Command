
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_e2be244cfbac267bf9a41230ae59553a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5a1eb0343590d6915ba5b22f68c41852 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["margin"] : "0 12px 8px", ["padding"] : "11px", ["background"] : "#818cf8", ["color"] : "#fff", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["gap"] : "8px", ["boxShadow"] : "0 4px 14px #818cf859", ["&:hover"] : ({ ["opacity"] : "0.9" }), ["&:active"] : ({ ["transform"] : "scale(0.98)" }) }),onClick:on_click_5a1eb0343590d6915ba5b22f68c41852},children)
    )
});
