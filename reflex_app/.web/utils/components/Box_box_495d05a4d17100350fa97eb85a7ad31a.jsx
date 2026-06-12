
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_495d05a4d17100350fa97eb85a7ad31a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5a1eb0343590d6915ba5b22f68c41852 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "50px", ["height"] : "50px", ["borderRadius"] : "50%", ["background"] : "#818cf8", ["color"] : "#fff", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["fontSize"] : "26px", ["fontWeight"] : "300", ["cursor"] : "pointer", ["margin"] : "0 8px 0 4px", ["flexShrink"] : "0", ["boxShadow"] : "0 4px 16px #818cf880", ["&:active"] : ({ ["transform"] : "scale(0.93)" }) }),onClick:on_click_5a1eb0343590d6915ba5b22f68c41852},children)
    )
});
