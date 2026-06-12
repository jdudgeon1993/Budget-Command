
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_bf09bca7de6176ea9323f71a59df623d = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5a1eb0343590d6915ba5b22f68c41852 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Add transaction",className:"mobile-fab",css:({ ["width"] : "52px", ["height"] : "52px", ["borderRadius"] : "50%", ["background"] : "#BF5AF2", ["color"] : "#fff", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["cursor"] : "pointer", ["flexShrink"] : "0", ["marginBottom"] : "4px", ["&:active"] : ({ ["transform"] : "scale(0.92)" }) }),onClick:on_click_5a1eb0343590d6915ba5b22f68c41852,role:"button",tabIndex:0},children)
    )
});
